ckan.module('ogdch_qualified_relations_add_rows', function ($) {
  return {
    initialize: function () {
      $("#ogdch_qualified_relations_add_row").click(function () {
        var firstHiddenRow = $("[id^='field-qualified-relation-']")
          .parent('.controls')
          .parent('.form-group.ogdch-hide-row')
          .first();
        firstHiddenRow.addClass("ogdch-show-row");
        $('.ogdch-show-row').removeClass('ogdch-hide-row');
        $( "#field-qualified-relation-1" ).focus();
      });
    }
  };
});
