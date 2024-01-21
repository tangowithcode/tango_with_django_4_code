$(document).ready(function() {
    feather.replace();

    $('#like_btn').click(function() {
     var catecategoryIdVar;
      catecategoryIdVar = $(this).attr('data-categoryid');
           
    $.get('/rango/like_category/',
     {'category_id': catecategoryIdVar},
      function(data) {
       $('#like_count').html(data);
       $('#like_btn').hide();
      })
    });
   });