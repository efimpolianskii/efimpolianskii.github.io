// Get the progress bar
var progressBar = document.getElementById("myBar");

// Get the navbar height
var navbarHeight = document.querySelector(".navbar").offsetHeight;

// Update the progress bar as the user scrolls
window.onscroll = function() {updateProgressBar()};

function updateProgressBar() {
  // Get the current position of the scroll
  var scrollPosition = document.documentElement.scrollTop || document.body.scrollTop;

  // Get the total height of the content
  var totalHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;

  // Calculate the progress percentage
  var progressPercentage = (scrollPosition / totalHeight) * 100;

  // Update the progress bar width
  progressBar.style.width = progressPercentage + "%";
}
