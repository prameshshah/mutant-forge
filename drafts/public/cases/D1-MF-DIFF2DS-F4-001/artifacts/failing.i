# Written for mutant-forge. Draft base problem.
# 2-D steady diffusion with a constant source.
[Mesh]
  type = GeneratedMesh
  dim = 2
  nx = 4
  ny = 4
  xmax = 1
  ymax = 1
[]

[Variables]
  [u]
  []
[]

[Kernels]
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


[Executioner]
  type = Steady
  solve_type = NEWTON
  petsc_options = '-ksp_converged_reason'
[]

[Outputs]
  exodus = false
[]
