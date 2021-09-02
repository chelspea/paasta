import mock

from paasta_tools.kubernetes_tools import registration_prefixed
from paasta_tools.setup_istio_mesh import cleanup_kube_svc
from paasta_tools.setup_istio_mesh import PAASTA_NAMESPACE
from paasta_tools.setup_istio_mesh import sanitise_kubernetes_service_name
from paasta_tools.setup_istio_mesh import setup_paasta_namespace_services
from paasta_tools.setup_istio_mesh import setup_unified_service
from paasta_tools.setup_istio_mesh import UNIFIED_K8S_SVC_NAME
from paasta_tools.setup_istio_mesh import UNIFIED_SVC_PORT


MOCK_PORT_NUMBER = 20508


def test_setup_kube_service():
    mock_client = mock.Mock()
    service_name = "compute-infra-test-service.main"
    mock_paasta_namespaces = {service_name: {"port": 20508}}
    sanitized_service_name = sanitise_kubernetes_service_name(service_name)

    setup_paasta_namespace_services(
        kube_client=mock_client, paasta_namespaces=mock_paasta_namespaces
    )

    assert mock_client.core.create_namespaced_service.call_count == 1
    assert (
        mock_client.core.create_namespaced_service.call_args[0][1].metadata.name
        == sanitized_service_name
    )
    assert mock_client.core.create_namespaced_service.call_args[0][1].spec.selector == {
        registration_prefixed(service_name): "true"
    }


def test_setup_unified_service():
    mock_client = mock.Mock()

    mock_port_list = [MOCK_PORT_NUMBER]

    setup_unified_service(kube_client=mock_client, port_list=mock_port_list)

    assert mock_client.core.create_namespaced_service.call_count == 1
    assert (
        len(mock_client.core.create_namespaced_service.call_args[0][1].spec.ports) == 2
    )
    assert (
        mock_client.core.create_namespaced_service.call_args[0][1].spec.ports[0].port
        == UNIFIED_SVC_PORT
    )
    assert (
        mock_client.core.create_namespaced_service.call_args[0][1].spec.ports[1].port
        == MOCK_PORT_NUMBER
    )


def test_cleanup_kube_svc_garbage_collect_services():
    mock_client = mock.Mock()
    mock_smartstack_namespaces = {"svc1", "svc2"}

    mock_existing_svc_names = {"svc1", "svc2", "svc3"}
    cleanup_kube_svc(mock_client, mock_smartstack_namespaces, mock_existing_svc_names)

    expected = [mock.call(name="svc3", namespace=PAASTA_NAMESPACE)]
    assert len(mock_client.core.delete_namespaced_service.call_args_list) == 1

    assert mock_client.core.delete_namespaced_service.call_args_list == expected


def test_cleanup_kube_svc_does_not_remove_unified_svc():
    mock_client = mock.Mock()
    mock_smartstack_namespaces = {"svc1", "svc2"}

    mock_existing_svc_names = {"svc1", "svc2", "svc3", UNIFIED_K8S_SVC_NAME}
    cleanup_kube_svc(mock_client, mock_smartstack_namespaces, mock_existing_svc_names)

    assert len(mock_client.core.delete_namespaced_service.call_args_list) == 1
    call_args, call_kwargs = mock_client.core.delete_namespaced_service.call_args_list[
        0
    ]
    assert call_kwargs["name"] != UNIFIED_K8S_SVC_NAME


def test_cleanup_kube_svc_does_not_remove_svc_while_running_first_time():
    mock_client = mock.Mock()
    mock_smartstack_namespaces = {"svc1", "svc2"}

    mock_existing_svc_names = {}
    cleanup_kube_svc(mock_client, mock_smartstack_namespaces, mock_existing_svc_names)
    assert not mock_client.core.delete_namespaced_service.called
