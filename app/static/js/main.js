/**
 * Created by toruitas on 1/26/16.
 */
$(document).ready(function(){

    var moveFooter = function() {
        $ft = $('#footer');
        $wrp = $('#wrapper');
        $($ft).css('position','relative');  //make sure it starts at the bottom to measure
        if($(window).height() > $($wrp).height()){
            $($ft).css('position','absolute');
            // sets wrapper height to window height so color reaches bottom
            $($wrp).css('height',$(window).height());
        }else{
            $($ft).css('position','relative');
            $($wrp).css('height','100%');
        }
    };


    (function(){
        moveFooter();

        $(window).resize(function() {
            moveFooter();
        });

    }());

    $('.flashes').fadeOut(5000);

    var hrefScrollToAnchor = function(url,anchor){

    }


});