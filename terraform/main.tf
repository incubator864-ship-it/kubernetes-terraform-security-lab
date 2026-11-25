terraform {
  required_version = ">= 1.6, < 2.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.37.0"
    }
  }
}

# Explicit context prevents accidental changes to a work cluster.
provider "kubernetes" {
  config_path    = pathexpand("~/.kube/config")
  config_context = "kind-security-lab"
}

resource "kubernetes_namespace_v1" "lab" {
  metadata {
    name = "security-lab"
    labels = {
      "pod-security.kubernetes.io/enforce" = "restricted"
      "pod-security.kubernetes.io/audit"   = "restricted"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}

resource "kubernetes_service_account_v1" "app" {
  metadata {
    name      = "lab-app"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
  }
  automount_service_account_token = false
}

resource "kubernetes_deployment_v1" "app" {
  timeouts {
    create = "2m"
    update = "2m"
  }
  metadata {
    name      = "lab-app"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
  }
  spec {
    replicas = 2
    selector {
      match_labels = { app = "lab-app" }
    }
    template {
      metadata {
        labels = { app = "lab-app" }
      }
      spec {
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
          name    = "app"
          image   = "busybox:1.37.0"
          command = ["/bin/sh", "-c", "while true; do echo lab-heartbeat; sleep 30; done"]
          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities {
              drop = ["ALL"]
            }
          }
          resources {
            requests = { cpu = "10m", memory = "16Mi" }
            limits   = { cpu = "100m", memory = "32Mi" }
          }
        }
      }
    }
  }
}

resource "kubernetes_role_v1" "observer" {
  metadata {
    name      = "lab-observer"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
  }
  rule {
    api_groups = [""]
    resources  = ["pods", "pods/log"]
    verbs      = ["get", "list", "watch"]
  }
}

resource "kubernetes_role_binding_v1" "observer" {
  metadata {
    name      = "lab-observer"
    namespace = kubernetes_namespace_v1.lab.metadata[0].name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role_v1.observer.metadata[0].name
  }
  subject {
    kind      = "User"
    name      = "lab-observer"
    api_group = "rbac.authorization.k8s.io"
  }
}
