ckan.module('ogdch_contact_points_add_rows', function ($) {
  return {
    initialize: function () {
      $("#ogdch_contact_points_add_row").click(function () {
        var firstHiddenRow = $("[id^='field-contact-point-']")
          .parent('.controls')
          .parent('.form-group.ogdch-hide-row')
          .slice(0, 2)
        firstHiddenRow.addClass("ogdch-show-row");
        $('.ogdch-show-row').removeClass('ogdch-hide-row');
        $( "#field-contact-point-name-1" ).focus();
      });
    }
  };
});