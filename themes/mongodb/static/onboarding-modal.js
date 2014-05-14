$(function() {

    var modalOptions = {
        show: true,
        backdrop: 'static',
        keyboard: false
    };

    var $onboardingModal = $('#onboarding-modal');

    var mmsPath = $.cookie('mms_path');
    if (!mmsPath) {
        $onboardingModal.modal(modalOptions);
    }

    $('.is-hosted, .is-on-prem').on('click', function(e) {
        e.preventDefault();

        var $target = $(e.currentTarget);
        saveSelection($target.data('path'), $target.hasClass('current'));
    });

    $(".mms-version-selector").on('click', function(e) {
        e.preventDefault();
        var path = $(e.currentTarget).data('path');
        $.cookie('mms_path', path);

        $('.option-popup .saving-copy').removeClass('hide');
        $('.mms-version-btn-group').addClass('hide');
        window.setTimeout(function() {
            window.docsRedirect(path);
        }, 1500);
    });

    var saveSelection = function(path, isCurrent) {
        var fn;

        $.cookie('mms_path', path);

        $('#onboarding-modal .action-buttons').addClass('hide');
        if (isCurrent) {
            $('#onboarding-modal .saving-copy').removeClass('hide');
            fn = function() {
                $onboardingModal.modal('hide');
            };
        } else {
            $('#onboarding-modal .redirect-copy').removeClass('hide');
            fn = function() {
                window.docsRedirect(path);
            };
        }

        window.setTimeout(fn, 1500);
    };
});