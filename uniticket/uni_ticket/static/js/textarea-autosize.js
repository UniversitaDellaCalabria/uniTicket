//(function($) {
    //$.fn.autogrow = function() {
        //return this.each(function() {
            //var textarea = this;
            //$.fn.autogrow.resize(textarea);
            //$(textarea).focus(function() {
                //textarea.interval = setInterval(function() {
                    //$.fn.autogrow.resize(textarea);
                //}, 500);
            //}).blur(function() {
                //clearInterval(textarea.interval);
            //});
        //});
    //};
    //$.fn.autogrow.resize = function(textarea) {
        //var lineHeight = parseInt($(textarea).css('line-height'), 10);
        //var lines = textarea.value.split('\n');
        //var columns = textarea.cols;
        //var lineCount = 0;
        //$.each(lines, function() {
            //lineCount += Math.ceil(this.length / columns) || 1;
        //});
        //var height = lineHeight * (lineCount + 1);
        //$(textarea).css('height', height);
    //};
//})(jQuery);

//$('textarea').autogrow();

function autogrow(textarea){
    textarea.style.boxSizing = 'border-box';
    var offset = textarea.offsetHeight - textarea.clientHeight;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + offset + 'px';

    textarea.addEventListener('input', function (event) {
        event.target.style.height = 'auto';
        event.target.style.height = event.target.scrollHeight + offset + 'px';
    });
    textarea.addEventListener('focus', function (event) {
        event.target.style.height = 'auto';
        event.target.style.height = event.target.scrollHeight + offset + 'px';
    });
}

document.querySelectorAll('textarea').forEach(function (element) {
    autogrow(element);
});
