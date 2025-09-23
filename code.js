var nodes = null;
var edges = null;
var network = null;

var DIR = "../img/refresh-cl/";
var EDGE_LENGTH_MAIN = 150;
var EDGE_LENGTH_SUB = 50;

// Called when the Visualization API is loaded.
function draw() {
  // Create a data table with nodes.
  nodes = [];

  // Create a data table with links.
  edges = [];

  nodes.push({
    id: 1,
    label: "Main",
    image: DIR + "Network-Pipe-icon.png",
    shape: "image",
    opacity: 0.7,
  });
  nodes.push({
    id: 2,
    label: "Office",
    image: DIR + "Network-Pipe-icon.png",
    shape: "image",
  });
  nodes.push({
    id: 3,
    label: "Wireless",
    image: DIR + "Network-Pipe-icon.png",
    shape: "image",
  });
  nodes.push({ id: 22, label: "Normal", opacity: 1 });
  edges.push({ from: 1, to: 2, length: EDGE_LENGTH_MAIN });
  edges.push({ from: 1, to: 3, length: EDGE_LENGTH_MAIN });
  edges.push({ from: 1, to: 22, length: EDGE_LENGTH_MAIN });

  for (var i = 4; i <= 7; i++) {
    nodes.push({
      id: i,
      label: "Computer",
      image: "https://cdn-icons-png.flaticon.com/512/684/684831.png",
      shape: "image",
      group: "computer",
      opacity: 1,
    });
    edges.push({ from: 2, to: i, length: EDGE_LENGTH_SUB });
  }

  nodes.push({
    id: 101,
    label: "Printer",
    image: "https://cdn-icons-png.flaticon.com/512/2543/2543409.png",
    shape: "image",
  });
  edges.push({ from: 2, to: 101, length: EDGE_LENGTH_SUB });


  

  // create a network
  var container = document.getElementById("mynetwork");
  var data = {
    nodes: nodes,
    edges: edges,
  };
  var options = {
    // nodes: {
    //   opacity: .5
    // },
    groups: {
      computer: {
        opacity: 0.3,
      },
    },
  };
  network = new vis.Network(container, data, options);
}

window.addEventListener("load", () => {
  draw();
});
   