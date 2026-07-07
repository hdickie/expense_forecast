<!DOCTYPE html>
<html>
 
<head>
    <title>DOM ProgressEvent</title>
</head>
 
<body>
    <h1 style="color:green;">
          GeeksforGeeks
      </h1>
    Progress Bar:
    <progress id="geeks"
              style="width:400px;">
    </progress>
 
    <script>
        let progressBar = document.getElementById("geeks"),
            client = new XMLHttpRequest();
        client.open("GET", "magical-unicorns");
        client.onprogress = function (pe) {
            if (pe.lengthComputable) {
                progressBar.max = pe.total;
                progressBar.value = pe.loaded;
            }
        }
        client.onloadend = function (pe) {
            progressBar.value = pe.loaded;
        }
        client.send();
    </script>
 
</body>
 
</html>