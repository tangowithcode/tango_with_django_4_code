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

    $('#search-input').keyup(function() {
        var query;
        query = $(this).val();
           
        $.get('/rango/suggest/',
         {'suggestion': query},
          function(data) {
           $('#categories-listing').html(data);
          })
       });
       
   });