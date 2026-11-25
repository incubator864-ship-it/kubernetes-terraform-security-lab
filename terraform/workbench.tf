resource "kubernetes_cron_job_v1" "workbench" {
  metadata {
    name      = "detection-workbench"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
  }
  spec {
    schedule                      = "*/15 * * * *"
    suspend                       = true
    concurrency_policy            = "Forbid"
    successful_jobs_history_limit = 1
    failed_jobs_history_limit     = 1
    job_template {
      metadata {}
      spec {
        backoff_limit           = 0
        active_deadline_seconds = 120
        template {
          metadata {
            labels = { app = "detection-workbench" }
          }
          spec {
            restart_policy                  = "Never"
            service_account_name            = kubernetes_service_account_v1.app.metadata[0].name
            automount_service_account_token = false
            security_context {
              run_as_non_root = true
              run_as_user     = 65532
              run_as_group    = 65532
              seccomp_profile {
                type = "RuntimeDefault"
              }
            }
            container {
              name              = "workbench"
              image             = "detection-workbench:lab"
              image_pull_policy = "Never"
              args              = ["--source", "examples/evaluable.json", "--ingested", "examples/evaluable.json"]
              security_context {
                allow_privilege_escalation = false
                read_only_root_filesystem  = true
                capabilities {
                  drop = ["ALL"]
                }
              }
              resources {
                requests = { cpu = "50m", memory = "32Mi" }
                limits   = { cpu = "250m", memory = "128Mi" }
              }
            }
          }
        }
      }
    }
  }
}
