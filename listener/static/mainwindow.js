$(document).ready( function() {
    var final_results = $( '.final-results' );
    var configure_final_result = function( display, record ) {
        display.data('final-result-record', record);
        display.find( '[data-property=uttid]').text( record.uttid);
        display.find( '[data-property=text]').text( record.text);
        display.find( '[data-action]').each( function( clickable ) {
            var element = $(this);
            element.click( function( evt ) {
                window.gui_bridge.js_event( JSON.stringify({
                    'action': element.attr('data-action'),
                    'record': record,
                }));
            });
        });
    };
    add_final = function( final_record ) {
        var item = $('.templates .final-result-item' ).clone();
        configure_final_result( item, final_record );
        final_results.append( item );
    };
});
