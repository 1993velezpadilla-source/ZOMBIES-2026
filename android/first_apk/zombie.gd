extends CharacterBody3D
## Original procedural prototype enemy, not a ripped COD model/animation.

signal eliminated(points: int)

var target: CharacterBody3D
var hp := 80
var move_speed := 1.55
var attack_timer := 0.0
var alive := true
var body_material: StandardMaterial3D

func configure(new_target: CharacterBody3D, wave: int) -> void:
	target = new_target
	hp = 65 + wave * 19
	move_speed = minf(3.25, 1.55 + float(wave) * 0.085)

func _ready() -> void:
	add_to_group("z2026_enemies")
	var collision := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.42
	capsule.height = 1.85
	collision.shape = capsule
	add_child(collision)
	var torso := MeshInstance3D.new()
	var torso_mesh := CapsuleMesh.new()
	torso_mesh.radius = 0.37
	torso_mesh.height = 1.62
	torso.mesh = torso_mesh
	body_material = StandardMaterial3D.new()
	body_material.albedo_color = Color(0.28, 0.33, 0.30)
	torso.material_override = body_material
	add_child(torso)
	var head := MeshInstance3D.new()
	var head_mesh := SphereMesh.new()
	head_mesh.radius = 0.29
	head_mesh.height = 0.56
	head.mesh = head_mesh
	head.position = Vector3(0, 0.94, 0)
	head.material_override = _mat(Color(0.49, 0.48, 0.43))
	add_child(head)
	for side in [-1.0, 1.0]:
		var eye := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = 0.077
		sphere.height = 0.15
		eye.mesh = sphere
		eye.position = Vector3(side * 0.115, 0.97, -0.258)
		eye.material_override = _mat(Color(1.0, 0.22, 0.13))
		add_child(eye)

func _mat(tint: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = tint
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return material

func _physics_process(delta: float) -> void:
	if not alive or target == null:
		return
	var parent_game := get_parent()
	if not parent_game.get("started"):
		return
	attack_timer = maxf(0.0, attack_timer - delta)
	var towards := target.global_position - global_position
	towards.y = 0
	if towards.length() > 1.12:
		var dir := towards.normalized()
		velocity.x = dir.x * move_speed
		velocity.z = dir.z * move_speed
		look_at(Vector3(target.global_position.x, global_position.y, target.global_position.z), Vector3.UP)
	else:
		velocity.x = 0
		velocity.z = 0
		if attack_timer <= 0.0:
			attack_timer = 1.45
			if parent_game.has_method("receive_damage"):
				parent_game.receive_damage(10)
	if is_on_floor():
		velocity.y = -0.1
	else:
		velocity.y -= 24.0 * delta
	move_and_slide()

func take_damage(amount: int) -> void:
	if not alive:
		return
	hp -= amount
	body_material.albedo_color = Color(0.66, 0.2, 0.18)
	if hp <= 0:
		alive = false
		remove_from_group("z2026_enemies")
		eliminated.emit(100)
		queue_free()
	else:
		get_tree().create_timer(0.16).timeout.connect(_reset_color)

func _reset_color() -> void:
	if alive and body_material != null:
		body_material.albedo_color = Color(0.28, 0.33, 0.30)
