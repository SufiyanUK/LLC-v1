// Main JavaScript file for Alert Pipeline Web App

$(document).ready(function() {
    // Global variables
    let pipelineCheckInterval = null;
    
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Run Pipeline Button Click
    $('#runPipelineBtn').click(function() {
        $('#pipelineModal').modal('show');
    });
    
    // Start Pipeline
    $('#startPipelineBtn').click(function() {
        const daysBack = $('#daysBack').val();
        const maxCredits = $('#maxCredits').val();
        const useCache = $('#useCache').is(':checked');
        
        // Disable form and show progress
        $('#pipelineForm').hide();
        $('#pipelineProgress').show();
        $('#startPipelineBtn').prop('disabled', true);
        
        // Send request to run pipeline
        $.ajax({
            url: '/api/run-pipeline',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                days_back: parseInt(daysBack),
                max_credits: parseInt(maxCredits),
                use_cache: useCache
            }),
            success: function(response) {
                if (response.success) {
                    // Start checking pipeline status
                    checkPipelineStatus();
                    pipelineCheckInterval = setInterval(checkPipelineStatus, 2000);
                } else {
                    showError(response.error || 'Failed to start pipeline');
                    resetPipelineModal();
                }
            },
            error: function(xhr) {
                showError('Error starting pipeline: ' + (xhr.responseJSON?.error || 'Unknown error'));
                resetPipelineModal();
            }
        });
    });
    
    // Check Pipeline Status
    function checkPipelineStatus() {
        $.ajax({
            url: '/api/pipeline-status',
            method: 'GET',
            success: function(status) {
                // Update progress bar
                $('.progress-bar').css('width', status.progress + '%')
                                  .text(status.progress + '%');
                $('#progressMessage').text(status.message);
                
                // Update dashboard status if on dashboard page
                if ($('#pipelineStatus').length) {
                    if (status.is_running) {
                        $('#pipelineStatus').removeClass('bg-success').addClass('bg-warning').text('Running');
                    } else {
                        $('#pipelineStatus').removeClass('bg-warning').addClass('bg-success').text('Ready');
                    }
                    $('#pipelineMessage').text(status.message);
                }
                
                // Check if completed
                if (!status.is_running && status.progress === 100) {
                    clearInterval(pipelineCheckInterval);
                    setTimeout(function() {
                        $('#pipelineModal').modal('hide');
                        showSuccess('Pipeline completed successfully!');
                        // Reload page to show new results
                        setTimeout(function() {
                            location.reload();
                        }, 2000);
                    }, 1000);
                } else if (!status.is_running && status.progress === 0) {
                    // Pipeline failed
                    clearInterval(pipelineCheckInterval);
                    showError('Pipeline failed: ' + status.message);
                    resetPipelineModal();
                }
            },
            error: function() {
                // Continue checking even if there's an error
                console.error('Error checking pipeline status');
            }
        });
    }
    
    // Reset Pipeline Modal
    function resetPipelineModal() {
        $('#pipelineForm').show();
        $('#pipelineProgress').hide();
        $('#startPipelineBtn').prop('disabled', false);
        $('.progress-bar').css('width', '0%').text('0%');
        $('#progressMessage').text('Starting pipeline...');
    }
    
    // Modal cleanup on close
    $('#pipelineModal').on('hidden.bs.modal', function() {
        if (pipelineCheckInterval) {
            clearInterval(pipelineCheckInterval);
        }
        resetPipelineModal();
    });
    
    // Show success message
    function showSuccess(message) {
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" style="z-index: 9999;">
                <i class="fas fa-check-circle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $('body').append(alertHtml);
        setTimeout(function() {
            $('.alert-success').fadeOut(function() {
                $(this).remove();
            });
        }, 5000);
    }
    
    // Show error message
    function showError(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" style="z-index: 9999;">
                <i class="fas fa-exclamation-triangle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        $('body').append(alertHtml);
        setTimeout(function() {
            $('.alert-danger').fadeOut(function() {
                $(this).remove();
            });
        }, 5000);
    }
    
    // Format dates
    $('.date-format').each(function() {
        const date = new Date($(this).text());
        if (!isNaN(date)) {
            $(this).text(date.toLocaleDateString());
        }
    });
    
    // Auto-refresh dashboard statistics
    if (window.location.pathname === '/') {
        setInterval(function() {
            updateDashboardStats();
        }, 30000); // Every 30 seconds
    }
    
    // Update dashboard statistics
    function updateDashboardStats() {
        $.ajax({
            url: '/api/stats',
            method: 'GET',
            success: function(stats) {
                // Update statistics cards
                $('.card-text').each(function() {
                    const parent = $(this).closest('.card');
                    if (parent.find('.card-title:contains("Total Companies")').length) {
                        $(this).text(stats.total_companies);
                    } else if (parent.find('.card-title:contains("Level 3")').length) {
                        $(this).text(stats.level_3_alerts);
                    } else if (parent.find('.card-title:contains("Level 2")').length) {
                        $(this).text(stats.level_2_alerts);
                    } else if (parent.find('.card-title:contains("Level 1")').length) {
                        $(this).text(stats.level_1_alerts);
                    }
                });
            },
            error: function(xhr) {
                console.error('Error updating statistics:', xhr.responseText);
            }
        });
    }
    
    // Company search/filter (if on companies page)
    if ($('#companiesTable').length && !$.fn.DataTable.isDataTable('#companiesTable')) {
        // DataTable will handle search/filter
    }
    
    // Alert search/filter (if on alerts page)
    if ($('#alertsTable').length && !$.fn.DataTable.isDataTable('#alertsTable')) {
        // DataTable will handle search/filter
    }
    
    // Keyboard shortcuts
    $(document).keydown(function(e) {
        // Ctrl+P or Cmd+P to run pipeline
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            $('#runPipelineBtn').click();
        }
        // Escape to close modals
        if (e.key === 'Escape') {
            $('.modal').modal('hide');
        }
    });
    
    // Handle connection errors gracefully
    $(document).ajaxError(function(event, xhr, settings, error) {
        if (xhr.status === 0) {
            console.error('Connection lost. Please check your internet connection.');
        } else if (xhr.status === 500) {
            console.error('Server error. Please try again later.');
        }
    });
    
    // Clean up intervals on page unload
    $(window).on('beforeunload', function() {
        if (pipelineCheckInterval) {
            clearInterval(pipelineCheckInterval);
        }
    });
});