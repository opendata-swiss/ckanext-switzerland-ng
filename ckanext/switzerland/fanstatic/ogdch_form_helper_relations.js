ckan.module('ogdch_relations_add_rows', function ($) {
  return {
    initialize: function () {
      $("#ogdch_relations_add_row").click(function () {
        var firstHiddenRows = $("[id^='field-relation-']")
          .parent('.controls')
          .parent('.form-group.ogdch-hide-row')
          .slice(0, 5);
        firstHiddenRows.addClass('ogdch-show-row');
        var firstHiddenLabel = $('.relation-label.ogdch-hide-row')
            .slice(0, 1);
        firstHiddenLabel.addClass('ogdch-show-row')
        $('.ogdch-show-row').removeClass('ogdch-hide-row');
        $( "#field-relation-title-1" ).focus();
      });
    }
  };
});
