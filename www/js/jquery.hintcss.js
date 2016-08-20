(function ( $ ) {
 
    $.fn.hint = function( options ) {
        var settings = $.extend({
            position: "top"
        }, options );
        
        return this.addClass('hint--' + settings.position).attr('data-hint', settings.label);
    };
 
}( jQuery ));