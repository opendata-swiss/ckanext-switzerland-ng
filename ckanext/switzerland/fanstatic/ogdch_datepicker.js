this.ckan.module('ogdch_datepicker', function ($) {
    return {
        initialize: function () {
            $('.datepicker').datepicker({
                language: 'de'
            });
        }
    };
});
