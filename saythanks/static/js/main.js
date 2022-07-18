$(document).on("change", "#badge-format", function () {
  const selectedFormat = $("#badge-format").val();
  const username = $("#username").val();
  if (selectedFormat === "imageurl") {
    $("#badgeCode").val(
      "https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg"
    );
  } else if (selectedFormat === "markdown") {
    const svg =
      "[![Say Thanks!](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)]";
    const url = `(https://saythanks.io/to/${username})`;
    $("#badgeCode").val(svg + url);
  } else if (selectedFormat === "rst") {
    const line1 =
      ".. image:: https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg \n";
    const line2 = `   :target: https://saythanks.io/to/${username}`;
    $("#badgeCode").val(line1 + line2);
  }
});
