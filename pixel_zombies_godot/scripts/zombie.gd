extends CharacterBody3D

signal killed(enemy)

const WALK_SPEED := 1.75
const MAX_HEALTH := 100
var health := MAX_HEALTH
var target: CharacterBody3D
var attack_time := 0.0

func _ready() -> void:
    add_to_group("zombies")
    var capsule := CapsuleShape3D.new()
    capsule.radius = 0.33
    capsule.height = 1.72
    var collision := CollisionShape3D.new()
    collision.shape = capsule
    collision.position.y = 0.86
    add_child(collision)
    _body_piece(Vector3(0, 0.96, 0), Vector3(0.65, 1.06, 0.38), Color(0.24, 0.31, 0.24))
    _body_piece(Vector3(0, 1.65, 0), Vector3(0.42, 0.42, 0.42), Color(0.46, 0.54, 0.40))
    _body_piece(Vector3(-0.16, 1.68, -0.22), Vector3(0.08, 0.08, 0.05), Color(0.95, 0.15, 0.10))
    _body_piece(Vector3(0.16, 1.68, -0.22), Vector3(0.08, 0.08, 0.05), Color(0.95, 0.15, 0.10))

func _body_piece(offset: Vector3, dimensions: Vector3, tint: Color) -> void:
    var mesh := MeshInstance3D.new()
    var box := BoxMesh.new()
    box.size = dimensions
    mesh.mesh = box
    var mat := StandardMaterial3D.new()
    mat.albedo_color = tint
    mat.roughness = 1.0
    mesh.material_override = mat
    mesh.position = offset
    add_child(mesh)

func _physics_process(delta: float) -> void:
    if target == null or health <= 0 or target.health <= 0:
        velocity.x = 0
        velocity.z = 0
        return
    attack_time = maxf(0.0, attack_time - delta)
    var toward := target.global_position - global_position
    toward.y = 0
    var distance := toward.length()
    if distance > 1.25:
        var direction := toward.normalized()
        velocity.x = direction.x * WALK_SPEED
        velocity.z = direction.z * WALK_SPEED
        rotation.y = atan2(-direction.x, -direction.z)
    else:
        velocity.x = 0
        velocity.z = 0
        if attack_time <= 0.0:
            target.take_damage(10)
            attack_time = 1.1
    velocity.y -= 20.0 * delta
    move_and_slide()

func take_damage(amount: int) -> void:
    if health <= 0:
        return
    health -= amount
    if health <= 0:
        killed.emit(self)
        queue_free()
