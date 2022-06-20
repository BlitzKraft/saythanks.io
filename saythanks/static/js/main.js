$(document).on("change", "#badge-format", function () {
  var selectedFormat = $("#badge-format").val();
  var username = $("#username").val();
  if (selectedFormat === "imageurl") {
    $("#badgeCode").val(
      "https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg"
    );
  } else if (selectedFormat === "markdown") {
    $("#badgeCode").val(
      "[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io" +
        "/to/" +
        username +
        ")"
    );
  } else if (selectedFormat === "rst") {
    var line1 =
      ".. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg \n";
    var line2 = "   :target: https://saythanks.io/to/" + username;
    $("#badgeCode").val(line1 + line2);
  }
});
