$(document).on("change", "#badge-format", function () {
  var selectedFormat = $("#badge-format").val();
  var username = $("#username").val();
  if (selectedFormat === "imageurl") {
    $("#badgeCode").val(
      "https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg"
    );
  } else if (selectedFormat === "markdown") {
    let svg = 
        "[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)]";
    let url = `(https://saythanks.io/to/${username})`;
    $("#badgeCode").val(svg + url);
  } else if (selectedFormat === "rst") {
    let line1 =
      ".. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg \n";
    let line2 = `   :target: https://saythanks.io/to/${username}`;
    $("#badgeCode").val(line1 + line2);
  }
});
