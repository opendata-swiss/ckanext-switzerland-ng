this.ckan.module('ogdch_datepicker', function ($) {
    return {
        initialize: function () {
            /**
             * Local functions for de, en-GB, fr-CH and it-CH copied in from locales/
             * folder, because CKAN wouldn't recognise them as resources otherwise.
             */
            ;(function($){
                $.fn.datepicker.dates['de'] = {
                    days: ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"],
                    daysShort: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
                    daysMin: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
                    months: ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
                    monthsShort: ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"],
                    today: "Heute",
                    monthsTitle: "Monate",
                    clear: "Löschen",
                    weekStart: 1,
                    format: "dd.mm.yyyy"
                };
            }(jQuery));
            ;(function($){
                $.fn.datepicker.dates['en-GB'] = {
                    days: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                    daysShort: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                    daysMin: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"],
                    months: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
                    monthsShort: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                    today: "Today",
                    monthsTitle: "Months",
                    clear: "Clear",
                    weekStart: 1,
                    format: "dd/mm/yyyy"
                };
            }(jQuery));
            ;(function($){
                $.fn.datepicker.dates['fr'] = {
                    days: ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"],
                    daysShort: ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"],
                    daysMin: ["D", "L", "Ma", "Me", "J", "V", "S"],
                    months: ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
                    monthsShort: ["Jan", "Fév", "Mar", "Avr", "Mai", "Jui", "Jul", "Aou", "Sep", "Oct", "Nov", "Déc"],
                    today: "Aujourd'hui",
                    monthsTitle: "Mois",
                    clear: "Effacer",
                    weekStart: 1,
                    format: "dd.mm.yyyy"
                };
            }(jQuery));
            ;(function($){
                $.fn.datepicker.dates['it'] = {
                    days: ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"],
                    daysShort: ["Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"],
                    daysMin: ["Do", "Lu", "Ma", "Me", "Gi", "Ve", "Sa"],
                    months: ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"],
                    monthsShort: ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"],
                    today: "Oggi",
                    clear: "Cancella",
                    weekStart: 1,
                    format: "dd.mm.yyyy"
                };
            }(jQuery));
            /**
             * End copied code.
             */
            $('.datepicker-de').datepicker({
                language: 'de'
            });
            $('.datepicker-en').datepicker({
                language: 'en-GB'
            });
            $('.datepicker-fr').datepicker({
                language: 'fr'
            });
            $('.datepicker-it').datepicker({
                language: 'it'
            });
        }
    };
});
