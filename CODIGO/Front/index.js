

function getMap() {
  setInterval(function() {  
    // create an XMLHttpRequest object
      //var XMLHttpRequest = require('xhr2');
      try{
        const xhr = new XMLHttpRequest();
    
        // set the callback function to be executed when the request is complete
        xhr.onreadystatechange = function() {
          if (xhr.readyState === 4 && xhr.status === 200) {
            // process the result
            console.log(xhr.responseText);
            // parse the result as JSON
            const data = JSON.parse(xhr.responseText);

            // access the cities and quadrants properties
            const cities = data.cities;
            const quadrants = data.quadrants;
            const result = data.result;
            const map = data.map;

            if (result === true){
                // Print the cities and the map
                console.log(cities);
                console.log(quadrants);
                console.log(map);
                //document.getElementById('map').innerHTML = map;
                var displayMap = document.getElementById("map");
                displayMap.innerHTML = '';
                var mapElementTemplate = document.getElementById("map-element-template");
                for (let i = 0; i < map.length; i++) {
                  for (let j = 0; j < map[i].length; j++) {
                    var matrixElement = mapElementTemplate.content.cloneNode(true);
                    matrixElement.textContent = map[i][j];

                    displayMap.appendChild(matrixElement);
                  }
                  displayMap.appendChild(document.createElement('br'));

                }
            }

          }
        };
      
        // open a connection to the specified address
        xhr.open('GET', 'http://127.0.0.1:3000/map');
      
        // send the request
        xhr.send();
      }catch (error){
        console.error(error); // Log the error to the console
        document.getElementById('error-message').innerHTML = error.message;
      }
      
    }, 10000);
  }


/*   function getMap() {
    setInterval(function() {
      fetch("http://127.0.0.1:3000/map")
        .then(response => response.json())
        .then(data => {
          document.getElementById("result").innerHTML = JSON.stringify(data);
          document.getElementById("map").innerHTML = data.map;
        });
    }, 10000);
  } */
  

