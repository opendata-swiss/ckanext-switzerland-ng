// Add rows to ckan forms on request by pressing a button

"use strict";

ckan.module('ogdch_form_helper_add_rows', function ($) {
  return {
    initialize: function () {
      $("#ogdch_publishers_add_row").click(function () {
        var publisherRows = $("[id^='field-publishers-']")
          .parent('.controls')
          .parent('.form-group.ogdch-hide-row')
          .first();
        publisherRows.addClass("ogdch-show-row");
        $('.ogdch-show-row').removeClass('ogdch-hide-row');
        $( "#field-publishers-1" ).focus();
      });
    }
  };
});