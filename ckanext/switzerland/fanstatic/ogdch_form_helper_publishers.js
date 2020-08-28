"use strict";

ckan.module('ogdch_publishers_add_rows', function ($) {
  return {
    initialize: function () {
      $("#ogdch_publishers_add_row").click(function () {
        var firstHiddenRow = $("[id^='field-publishers-']")
          .parent('.controls')
          .parent('.form-group.ogdch-hide-row')
          .first();
        firstHiddenRow.addClass("ogdch-show-row");
        $('.ogdch-show-row').removeClass('ogdch-hide-row');
        $( "#field-publisher-1" ).focus();
      });
    }
  };
});
