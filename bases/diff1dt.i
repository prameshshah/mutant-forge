# Written for mutant-forge. Draft base problem.
# 1-D transient diffusion with a constant source.
[Mesh]
  type = GeneratedMesh
  dim = 1
  nx = 20
  xmax = 1
[]

[Variables]
  [u]
  []
[]

[Kernels]
  [time]
    type = TimeDerivative
    variable = u
  []
  [diffusion]
    type = Diffusion
    variable = u
  []
  [source]
    type = BodyForce
    variable = u
    value = 1
  []
[]

[BCs]
  [left]
    type = DirichletBC
    variable = u
    boundary = left
    value = 0
  []
  [right]
    type = DirichletBC
    variable = u
    boundary = right
    value = 0
  []
[]

[Executioner]
  type = Transient
  num_steps = 1
  dt = 1
  solve_type = NEWTON
  petsc_options = '-ksp_converged_reason'
[]

[Outputs]
  exodus = false
[]
