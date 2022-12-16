

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
                
                var city1 = document.getElementById("city1");
                var city2 = document.getElementById("city2");
                var city3 = document.getElementById("city3");
                var city4 = document.getElementById("city4");

                let i = 1;
                for (const key in cities) {
                  if (i === 1) {
                    city1.innerHTML = `${key}: ${cities[key]} ºC`;
                  } else if (i === 2) {
                    city2.innerHTML = `${key}: ${cities[key]} ºC`;
                  } else if (i === 3) {
                    city3.innerHTML = `${key}: ${cities[key]} ºC`;
                  } else if (i === 4) {
                    city4.innerHTML = `${key}: ${cities[key]} ºC`;
                  }
                  i++;

                }

                
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
      
    }, 1000);
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
  

