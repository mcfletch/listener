$(document).ready( function() {
    var final_results = $( '.final-results' );
    var gui_event = function( message ) {
        window.gui_bridge.send_event( JSON.stringify( message ));
    };
    var configure_final_result = function( display, record ) {
        display.data('final-result-record', record);
        display.find( '[data-property=uttid]').text( record.uttid);
        display.find( '[data-property=text]').text( record.text);
        display.find( '[data-action]').each( function( clickable ) {
            var element = $(this);
            element.click( function( evt ) {
                gui_event({
                    'action': element.attr('data-action'),
                    'record': record
                });
            });
        });
        display.find( '.original-recognition' ).on(
            'blur',
            function( evt ) {
                var element = $(this);
                var new_text = element.text();
                //new_text = new_text.replace( '\x1b','');
                if ( new_text !== record.text) {
                    gui_event({
                        'action': 'correction',
                        'record': 'record',
                        'text': new_text
                    });
                    element.addClass( 'corrected' );
                    record.text = new_text;
                };
            }
        ).on( 'keypress', function( evt ) {
            if(evt.which == 27) {
                var element = $(this);
                element.text( record.text );
                return false;
            } else {
                return true;
            }
        });
        return display;
    };
    var configure_nbest_result = function( display, final_record, nbest_record ) {
        display.data('final-result-record', final_record);
        display.data('nbest-record', nbest_record);
        display.find( '[data-property=text]' ).text( nbest_record );
        display.find( '[data-action]').each( function( clickable ) {
            var element = $(this);
            element.click( function( evt ) {
                window.gui_bridge.send_event( JSON.stringify({
                    'action': element.attr('data-action'),
                    'record': final_record,
                    'nbest_record': nbest_record
                }));
            });
        });
        return display;
    };
    add_final = function( final_record ) {
        var display = $('.templates .final-result-item' ).clone();
        var nbest_extra = 0;
        configure_final_result( display, final_record );
        $.map( final_record.nbest, function( nbest ) {
            if (nbest != final_record.text) {
                var nbest_display = configure_nbest_result( $('.templates .nbest-result-item').clone(), final_record, nbest );
                display.find( '.nbest' ).append( nbest_display );
                nbest_extra += 1;
            }
        });
        if (!nbest_extra) {
            display.find( '.nbest' ).hide();
        }
        final_results.append( display );
    };
});
