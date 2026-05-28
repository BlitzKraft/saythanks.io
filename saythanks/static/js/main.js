$(document).on("change", "#badge-format", () => {
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

// Function to handle URL encoding for topic parameters
function handleTopicUrlEncoding() {
  const currentUrl = window.location.href;
  const urlPattern = /\/to\/([^\/]+)&(.+)/;
  const match = currentUrl.match(urlPattern);

  if (match) {
    const [, inboxId, topic] = match;
    // Check if topic contains unencoded special characters
    if (topic !== encodeURIComponent(topic)) {
      const encodedTopic = encodeURIComponent(topic);
      const newUrl = `/to/${inboxId}&${encodedTopic}`;
      window.location.replace(newUrl);
    }
  }
}

// Function to handle URL fragments for topic parameters
function handleFragmentToTopic() {
  const hash = window.location.hash;
  const pathname = window.location.pathname;

  // Check if we're on a /to/ page with a fragment
  if (pathname.match(/^\/to\/[^\/]+\/?$/) && hash && hash.length > 1) {
    // Remove the # from hash for the URL parameter, but keep it for display
    const topicWithoutHash = hash.substring(1); // Remove the # symbol
    const topicForUrl = encodeURIComponent('#' + topicWithoutHash); // Add # back and encode
    const cleanPath = pathname.replace(/\/$/, ''); // Remove trailing slash
    const newUrl = `${cleanPath}&${topicForUrl}`;
    window.location.replace(newUrl);
  }
}

// Run URL encoding check when page loads
$(document).ready(() => {
  handleFragmentToTopic();
  //handleTopicUrlEncoding();
});
