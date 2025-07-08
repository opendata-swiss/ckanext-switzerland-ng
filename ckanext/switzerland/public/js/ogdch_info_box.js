ckan.module('ogdch_info_box', function ($) {
  return {
    initialize: function () {
      var locale = $('html')[0].lang
      $( "#ogdch_info_box h1" ).each(function( index ) {
        if ($( this ).text() !== locale) {
            $(this).nextUntil('h1').hide();
        }
        $(this).hide()
      });
    }
  };
});
