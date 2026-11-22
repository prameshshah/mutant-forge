# Written for mutant-forge. Draft base problem.
# 1-D transient nonlinear diffusion: the diffusivity grows with u, so Newton needs
# several iterations per step. MatDiffusion takes dD/du from the derivative material,
# so the Jacobian is exact without automatic differentiation.
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
  dt = 32
  solve_type = NEWTON
  petsc_options = '-ksp_converged_reason'
  nl_rel_tol = 1e-20
  nl_abs_tol = 1e-50
  nl_max_its = 20
  dtmin = 1
[]

[Outputs]
  exodus = false
[]
