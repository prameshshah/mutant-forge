# Written for mutant-forge. Draft base problem.
# 2-D transient nonlinear diffusion: the diffusivity grows with u, so Newton needs
# several iterations per step. MatDiffusion takes dD/du from the derivative material,
# so the Jacobian is exact without automatic differentiation.
[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 10
  ny = 10
  xmax = 1
  ymax = 1
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
    type = MatDiffusion
    variable = u
    diffusivity = D
  []
  [source]
    type = BodyForce
    variable = u
    value = 10
  []
[]

[Materials]
  [diffusivity]
    type = DerivativeParsedMaterial
    property_name = D
    coupled_variables = 'u'
    expression = '1 + 5 * u * u'
    # interpreted, not compiled at run time, so runs need no C++ compiler
    enable_jit = false
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
  dt = 4
  solve_type = NEWTON
  petsc_options = '-ksp_converged_reason'
  nl_max_its = 1
  dtmin = 1
[]

[Outputs]
  exodus = false
[]
