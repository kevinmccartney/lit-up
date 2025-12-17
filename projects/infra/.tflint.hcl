config {
  # If you use modules later, this keeps tflint usable without extra flags.
  call_module_type = "all"
}

# Enable recommended built-in rules (plugin rules are configured below).
rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_deprecated_interpolation" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = false
}

plugin "aws" {
  enabled = true
  version = "0.41.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

