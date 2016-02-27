/**
 * Created by toruitas on 2/13/16.
 */
$(document).ready(function() {
    $('button').click(function() {
    	var toAdd = $("input[name=message]").val();
        $('#messages').append("<p>"+toAdd+"</p>");
    });

    var $k = $('#krypton');

    //$($k).click(function(){
    //    $('#krypton').fadeOut('fast');
    //});

    $($k).dblclick(function(){
        $('#krypton').fadeOut('slow');
    });

    $($k).click(function(){
        $($k).effect('bounce',{times:2},200);
        $($k).effect('slide');
        $($k).effect('explode');
    });

    $('#hover').hover(
        function(){
            $(this).addClass('active');
        },
        function(){
            $(this).removeClass('active');
        }
      );

    $('input').focus(function(){
        $(this).css('outline-color','#F00');
    });

    $(document).keydown(function(key){ //pass it the key that was pressed
        $('div').animate({left:'+=10px'},500)
    });

    $("#menu").accordion({collapsible: true, active: false});

    $('#car').draggable();

    $('#animate').resizable();

    $('ol').selectable();
    $('ol').sortable();
});