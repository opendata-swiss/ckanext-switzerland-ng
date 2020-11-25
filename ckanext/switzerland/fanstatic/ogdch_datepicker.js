import './bootstrap-datepicker.min';
import './bootstrap-datepicker.min.css';
import '.locales/bootstrap-datepicker.de.min.css';
import '.locales/bootstrap-datepicker.fr-CH.min.css';
import '.locales/bootstrap-datepicker.it-CH.min.css';

this.ckan.module('ogdch_datepicker', function ($) {
    return {
        initialize: function () {
            $.fn.datepicker.dates.de={days:["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"],daysShort:["Son","Mon","Die","Mit","Don","Fre","Sam"],daysMin:["So","Mo","Di","Mi","Do","Fr","Sa"],months:["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"],monthsShort:["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"],today:"Heute",monthsTitle:"Monate",clear:"Löschen",weekStart:1,format:"dd.mm.yyyy"};

            $('.datepicker').datepicker({
                language: 'de'
            });
        }
    };
});
