this.ckan.module('ogdch_datepicker', function ($) {
    return {
        initialize: function () {
            /**
             * Local functions for de, fr-CH and it-CH copied in from locales/
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
            $('.datepicker').datepicker({
                language: 'fr'
            });
        }
    };
});
