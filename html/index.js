var camera, scene, renderer, object, stats, container, shape_material;
var mouseX = 0;
var mouseXOnMouseDown = 0;
var mouseY = 0;
var mouseYOnMouseDown = 0;
var moveForward = false;
var moveBackward = false;
var moveLeft = false;
var moveRight = false;
var moveUp = false;
var moveDown = false;
var windowHalfX = window.innerWidth / 2;
var windowHalfY = window.innerHeight / 2;
var selected_target_color_r = 0;
var selected_target_color_g = 0;
var selected_target_color_b = 0;
var selected_target = null;

var PIECES = {"table": {"top": [95.0, 40.0], "legs (2)": [26.5, 20.0], "leg bases (2)": [29.0, 4.5], "spanners (2)": [45.5, 6.0]}, "bench": {"top": [95.0, 15.0], "spanner": [68.0, 6.0], "legs (2)": [16.5, 15.0]}};

init();
animate();

function piecesDiv() {
	var pieces = document.createElement('div');
	for (var thingName in PIECES) {
		var thingH1 = document.createElement('h1');
		thingH1.innerText = thingName;
		pieces.appendChild(thingH1);
		var thing = PIECES[thingName];
		var ul = document.createElement('ul');
		for (var pieceName in thing) {
			var piece = thing[pieceName];
			var li = document.createElement('li');
			li.innerText = pieceName + ": " + piece[0] + " x " + piece[1];
			ul.appendChild(li);
		}
		pieces.appendChild(ul);
	}
	pieces.style.position = 'absolute';
	pieces.style.top = '12';
	pieces.style.left = '12';
	return pieces;
}

function init() {
  container = document.createElement('div');
  document.body.appendChild(container);

  camera = new THREE.PerspectiveCamera(
		50, window.innerWidth / window.innerHeight, 1, 200);
  controls = new THREE.OrbitControls(camera);
	camera.position.set(0, -100, 0);
	controls.update();

	container.appendChild(piecesDiv());

  // for selection
  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();

  // create scene
  scene = new THREE.Scene();
  scene.add(new THREE.AmbientLight(0x101010));
  directionalLight = new THREE.DirectionalLight(0xffffff);
  directionalLight.position.x = 1;
  directionalLight.position.y = -1;
  directionalLight.position.z = 2;
  directionalLight.position.normalize();
  scene.add(directionalLight);
  light1 = new THREE.PointLight(0xffffff);
  scene.add(light1);
  
  loader = new THREE.BufferGeometryLoader();
	table_material = new THREE.MeshPhongMaterial(
		{ color:0xa5a5a5, specular:0xffffff, shininess:0.9,});
	loader.load(
		'table.json',
		function(geometry) {
			mesh = new THREE.Mesh(geometry, table_material);
			scene.add(mesh);
			fit_to_scene();
		});

  renderer = new THREE.WebGLRenderer({antialias:true, alpha: true});
  renderer.setSize( window.innerWidth, window.innerHeight);
  container.appendChild(renderer.domElement);

  // for shadow rendering
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  // add events
  document.addEventListener('keypress', onDocumentKeyPress, false);
  // document.addEventListener('click', onDocumentMouseClick, false);
  window.addEventListener('resize', onWindowResize, false);
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  render();
}
function update_lights() {
  if (directionalLight != undefined) {
    directionalLight.position.copy(camera.position);
  }
}
function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}
function onDocumentKeyPress(event) {
  event.preventDefault();
  if (event.key=="t") {  // t key
    if (selected_target) {
      selected_target.material.visible = !selected_target.material.visible;
    }
  }

}
function onDocumentMouseClick(event) {
  event.preventDefault();
  mouse.x = ( event.clientX / window.innerWidth ) * 2 - 1;
  mouse.y = - ( event.clientY / window.innerHeight ) * 2 + 1;
  // restore previous selected target color
  if (selected_target) {
    selected_target.material.color.setRGB(selected_target_color_r,
																					selected_target_color_g,
																					selected_target_color_b);
  }
  // performe selection
  raycaster.setFromCamera(mouse, camera);
  var intersects = raycaster.intersectObjects(scene.children);
  if (intersects.length > 0) {
    var target = intersects[0].object;
    selected_target_color_r = target.material.color.r;
    selected_target_color_g = target.material.color.g;
    selected_target_color_b = target.material.color.b;
    target.material.color.setRGB(1., 0.65, 0.);
    console.log(target);
    selected_target = target;
  }
}
function fit_to_scene() {
  // compute bounding sphere of whole scene
  var center = new THREE.Vector3(0,0,0);
  var radiuses = new Array();
  var positions = new Array();
  // compute center of all objects
  scene.traverse(function(child) {
    if (child instanceof THREE.Mesh) {
      child.geometry.computeBoundingBox();
      var box = child.geometry.boundingBox;
      var curCenter = new THREE.Vector3().copy(box.min).
					add(box.max).multiplyScalar(0.5);
      var radius = new THREE.Vector3().copy(box.max).distanceTo(box.min)/2.;
      center.add(curCenter);
      positions.push(curCenter);
      radiuses.push(radius);
    }
  });
  if (radiuses.length > 0) {
    center.divideScalar(radiuses.length);
  }
  var maxRad = 1.;
  // compute bounding radius
  for (var ichild = 0; ichild < radiuses.length; ++ichild) {
    var distToCenter = positions[ichild].distanceTo(center);
    var totalDist = distToCenter + radiuses[ichild];
    if (totalDist > maxRad) {
      maxRad = totalDist;
    }
  }
  camera.lookAt(center);
  var direction = new THREE.Vector3().copy(camera.position).
			sub(controls.target);
  var len = direction.length();
  direction.normalize();
  
  // compute new distance of camera to middle of scene to fit the
	// object to screen
  var lnew = maxRad / Math.sin(camera.fov/180. * Math.PI / 2.);
  direction.multiplyScalar(lnew);
  
  var pnew = new THREE.Vector3().copy(center).add(direction);
  // change near far values to avoid culling of objects 
  camera.position.set(pnew.x, pnew.y, pnew.z);
  camera.far = lnew*50;
  camera.near = lnew*50*0.001;
  camera.updateProjectionMatrix();
  controls.target = center;
  controls.update();
}
function render() {
  //@IncrementTime@  TODO UNCOMMENT
  update_lights();
  renderer.render(scene, camera);
}
