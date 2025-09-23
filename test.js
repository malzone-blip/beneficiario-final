var DIR = "img/soft-scraps-icons/";

var nodes = null;
var edges = null;
var network = null;

// Called when the Visualization API is loaded.
function draw() {
  // create people.
  // value corresponds with the age of the person
  var DIR = "../img/indonesia/";
  nodes = [
    { id: 1, shape: "circularImage", image: "https://cdn-icons-png.flaticon.com/512/684/684831.png", physics: false, title: "Nodo 1" },
    { id: 2, shape: "circularImage", image:"https://cdn-icons-png.flaticon.com/512/2543/2543409.png" , physics: false},
 
    {
      id: 4,
      shape: "circularImage",
      image: "https://cdn-icons-png.flaticon.com/512/9292/9292785.png",
      label: "pictures by this guy!",
      fixed: true,
      title: 'generate text before binding the sets'
    },

    {
      id: 15,
      shape: "circularImage",
      image: DIR + "missing.png",
      brokenImage: "https://cdn-icons-png.flaticon.com/512/9292/9292777.png",
      label: "when images\nfail\nto load",
      title: '<div class="plus-icon">+</div>' + 'Nodo 1',
      x: 0,
      y: 60
    },    
    {
        id: 10,
        shape: "circularImage",
        image: DIR + "missing.png",
        brokenImage: "https://cdn-icons-png.flaticon.com/512/9292/9292777.png",
        label: "when images\nfail\nto load",
        title: '<div class="plus-icon">+</div>' + 'Nodo 1',
        x: 0,
        y: 60
      },

  ];

  // create connections between people
  // value corresponds with the amount of contact between two people
  edges = [
    { from: 1, to: 4 },
    { from: 2, to: 4 },
    { from: 3, to: 4 },
    { from: 15, to: 4 },
    { from: 4, to: 10 },

  ];

  // create a network
  var container = document.getElementById("mynetwork");
  var data = {
    nodes: nodes,
    edges: edges,
  };
  var options = {
    nodes: {
      borderWidth: 4,
      size: 30,
      color: {
        border: "#222222",
        background: "white",
      },
      font: { color: "Black" },
    },
    edges: {
      color: "lightgray",
    },
    interaction: {
        hover: true,
        hideEdgesOnDrag: true,
        tooltipDelay: 2,
        },
  };

  
  network = new vis.Network(container, data, options);

  network.on("selectNode", function (params) {
    if(params.nodes.length>0){
    // Eliminar el div anterior si existe
    var previousDiv = document.querySelector('.info-node-div');
    if (previousDiv) {
    previousDiv.remove();
    }
        // Obtener las coordenadas del div.vis-tooltip
        var tooltip = document.querySelector('.vis-tooltip');
        var tooltipRect = tooltip.getBoundingClientRect();
        var tooltipX = tooltipRect.left;
        var tooltipY = tooltipRect.top;
    
        // Crear el div con la información del nodo
        let div = document.createElement("div");
        div.innerHTML = "Información del nodo:<br>"+ params.nodes[0];
        div.classList.add("info-node-div");
        div.style.cssText = "position:absolute;left:"+tooltipX+"px;top:"+tooltipY+"px;background-color:red;padding:10px;";
        document.body.appendChild(div);
    }
  });
  network.on("deselectNode", function (params) {
    if (document.querySelector('.info-node-div')) {
        document.querySelector('.info-node-div').remove();
        }
    
});
network.on("dragEnd", function (params) {
    if (document.querySelector('.info-node-div')) {
        document.querySelector('.info-node-div').remove();
        }
});

network.on("doubleClick", function (params) {
    if(params.nodes.length>0){
        var nodeId = params.nodes[0];
        // Redirigir a una página específica utilizando el id del nodo
        window.location.href = "https://git.imp.fu-berlin.de/ivcondric/DBS-Project/-/blob/master/sigma.js-1.2.0/examples/edge-renderers.html" ;
    }
});

network.on("Click", function (params) {
    if(params.nodes.length>0){
        var nodeId = params.nodes[0];
        // Redirigir a una página específica utilizando el id del nodo
        window.location.href = "https://git.imp.fu-berlin.de/ivcondric/DBS-Project/-/blob/master/sigma.js-1.2.0/examples/edge-renderers.html" ;
    }
});
}





window.addEventListener("load", () => {
  draw();
});


/*  network.on("dragEnd", function (params) {
    var draggedNodeId = params.nodes[0];
    var nodePositions = network.getPositions([draggedNodeId]);
    var nodeX = nodePositions[draggedNodeId].x;
    var nodeY = nodePositions[draggedNodeId].y;
    var tooltip = document.querySelector('.vis-tooltip');
    var tooltipRect = tooltip.getBoundingClientRect();
    var tooltipX = tooltipRect.left;
    var tooltipY = tooltipRect.top;
    var infoNodeDiv = document.querySelector('.info-node-div');
    if (infoNodeDiv) {
        infoNodeDiv.style.left = tooltipX  + 'px';
        infoNodeDiv.style.top = tooltipY + 'px';
    }
});*/

/*
var selectedNode = nodes.get(params.nodes[0]);
var content = "Información del nodo:<br>" + selectedNode.title;
network.popup.setPosition(selectedNode.x, selectedNode.y);
network.popup.setText(content);
network.popup.show();*/

/*
network.on("selectNode", function (params) {
    if(params.nodes.length>0){
        var positions = network.getPositions();
        var selectedNode = positions[params.nodes[0]];
        alert("You clicked on node " + params.nodes[0] + " at position x: " + selectedNode.x + " y: " + selectedNode.y);
    }
});*/