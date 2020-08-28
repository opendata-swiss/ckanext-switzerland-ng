ckan.module('ogdch_see_alsos_add_rows', function ($) {
  return {
    initialize: function () {
      $("#ogdch_see_alsos_add_row").click(function () {
        var firstHiddenRow = $("[id^='field-see-also-']")
          .parent('.controls')
          .parent('.form-group.ogdch-hide-row')
          .first();
        firstHiddenRow.addClass("ogdch-show-row");
        $('.ogdch-show-row').removeClass('ogdch-hide-row');
        $( "#field-see-also-1" ).focus();
      });
    }
  };
});