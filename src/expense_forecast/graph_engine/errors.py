class UnsupportedGraphBehaviorError(ValueError):
    def __init__(self, unsupported):
        self.unsupported = list(unsupported)
        super().__init__(
            "Graph engine does not support: " + "; ".join(self.unsupported)
        )


class GraphConvergenceError(RuntimeError):
    def __init__(self, component, iterations, fingerprints):
        self.component = component
        self.iterations = iterations
        self.fingerprints = list(fingerprints)
        super().__init__(
            f"Graph component {component!r} did not converge after "
            f"{iterations} iterations"
        )


class GraphShadowMismatchError(AssertionError):
    def __init__(
        self, *, section, event=None, variable=None, graph_value=None,
        legacy_value=None, producer=None, provenance=None, downstream=None,
    ):
        self.section = section
        self.event = event
        self.variable = variable
        self.graph_value = graph_value
        self.legacy_value = legacy_value
        self.producer = producer
        self.provenance = list(provenance or [])
        self.downstream = list(downstream or [])
        super().__init__(
            f"Graph shadow mismatch in {section}: event={event!r} "
            f"variable={variable!r} graph={graph_value!r} "
            f"legacy={legacy_value!r} producer={producer!r}"
        )
