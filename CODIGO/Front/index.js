
function getGame() {
  // Create a flag variable to track the state of the server
  let serverDown = false;

  // Define a function to make the request
  function makeRequest() {
    // Check the value of the flag
    if (serverDown === true) {
      // Server is down, skip the request and schedule it to be made again after a delay
      setTimeout(makeRequest, 300000); // 5 minutes in milliseconds
      return;
    }
    
      try{
        // create an XMLHttpRequest object
        var xhr = new XMLHttpRequest();

        // set the callback function to be executed when the request is complete
        xhr.onload = function() {
          if (xhr.status >= 200 && xhr.status < 300) {
            // process the result
            console.log(xhr.responseText);
            // parse the result as JSON
            const data = JSON.parse(xhr.responseText);

            // access the cities and quadrants properties
            const result = data['result'];
            const cities = data['cities'];
            const map = data['map'];
            const npcs = data['npcs'];
            const players = data['players'];

            console.log(result);
            
            if (result === true){
                // Print the cities and the map
                console.log(cities);
                console.log(map);
                console.log(npcs);
                console.log(players);
                
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

                var displayNpcs = document.getElementById("npcs");
                displayNpcs.innerHTML = '';
                for(const key in npcs){
                  const npc = document.createElement('div');
                  npc.innerHTML = `${key}: level ${npcs[key]}`;
                  const parentElement = document.getElementById('npcs');
                  parentElement.appendChild(npc);
                }

                var displayPlayers = document.getElementById("players");
                displayPlayers.innerHTML = '';
                for(const key in players){
                  //Create the div element
                  const player = document.createElement('div');
                  // Obtain the rest of the data of the player
                  var list = data[key];
                  console.log(list)
                  var str = list[0] + ', Level: ' + list[1] + ', Total level: ' + list[2] + ', EC: ' + list[3] + ', EF: ' + list[4];
                  player.innerHTML = `${key} - ${str}, Position ${players[key]}`;
                  const parentElement = document.getElementById('players');
                  parentElement.appendChild(player);
                }

            }

          }else{
            //Error
            document.getElementById('error-message').innerHTML = "There was an error while making the request. Please try again in 5 minutes";
            serverDown = true;
            setTimeout(makeRequest, 300000); // 5 minutes in milliseconds
          }
        };

        xhr.onerror = function(){
            //Error
            console.log("The server is down. Please try again in 5 minutes");
            document.getElementById('error-message').innerHTML = "The server is down. Please try again in 5 minutes";
            serverDown = true;
            setTimeout(makeRequest, 300000); // 5 minutes in milliseconds
        };

        // open a connection to the specified address
        xhr.open('GET', 'http://127.0.0.1:3000/game', true);
      
        // send the request
        xhr.send();


      }catch (error){
        console.log(error);
        document.getElementById('error-message').innerHTML = "The server is down. Please try again in 5 minutes";
        serverDown = true;
        setTimeout(makeRequest, 300000); // 5 minutes in milliseconds
      }
    }

    // Schedule the request to be made every second
    setInterval(makeRequest, 10000);

  }