from second_brain.memory import AgentMemoryAdapter


def test_recall_merges_scopes_sorts_scores_and_truncates(monkeypatch):
    adapter = AgentMemoryAdapter("http://memory.test")
    requests = []
    responses = {
        "brain": [
            {"id": "brain-low", "score": 0.4, "namespace": "brain"},
            {"id": "brain-high", "score": 0.9, "namespace": "brain"},
        ],
        "paper-corpus": [
            {"id": "paper-tie-b", "score": 0.8, "namespace": "paper-corpus"},
            {"id": "paper-tie-a", "score": 0.8, "namespace": "paper-corpus"},
        ],
    }

    def request(method, path, payload):
        requests.append((method, path, payload))
        return responses[payload["namespace"]]

    monkeypatch.setattr(adapter, "_request", request)

    assert adapter.recall("claim", scopes=["brain", "paper-corpus"], k=3) == [
        {"id": "brain-high", "score": 0.9, "namespace": "brain"},
        {"id": "paper-tie-a", "score": 0.8, "namespace": "paper-corpus"},
        {"id": "paper-tie-b", "score": 0.8, "namespace": "paper-corpus"},
    ]
    assert requests == [
        ("POST", "/recall", {"query": "claim", "namespace": "brain", "k": 3}),
        ("POST", "/recall", {"query": "claim", "namespace": "paper-corpus", "k": 3}),
    ]
