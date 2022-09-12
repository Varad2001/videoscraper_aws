function add_data(response){
document.body.innerHTML = document.body.innerHTML + response;
}
function geturls(){
$.ajax({
      url: "/get_urls",
      type: "post",
      data: {jsdata: "ghj" },
      success: function(response) {
        add_data(response);
      },

      error: function(xhr) {
        //Do Something to handle error
      }
    });
}
function savedata(){
document.getElementById("info").innerHTML = "Saving...please wait...";
$.ajax({
      url: "/save_data",
      type: "post",
      data: {jsdata: "hj"},
      success: function(response) {
        add_data(response);
      },

      error: function(xhr) {
        //Do Something to handle error
      }
    });
}
function get_updates(){
$.ajax({
      url: "/get_updates",
      type: "post",
      data: {jsdata: "hj"},
      success: function(response) {
        add_data(response);
      },

      error: function(xhr) {
        //Do Something to handle error
      }
    });
}
