from types import SimpleNamespace


class FakeSt:
    def __init__(self, user_input=None):
        self._title_called = False
        self._messages_rendered = []
        self._spinners = []
        self._user_input = user_input
        self.session_state = {}
        self._current_role = None

    # UI primitives
    def title(self, *_args, **_kwargs):
        self._title_called = True

    def chat_message(self, role):
        # Context manager similar to Streamlit behavior
        class Ctx:
            def __init__(self, outer, role):
                self.outer = outer
                self.role = role

            def __enter__(self):
                self.outer._current_role = self.role
                return self.outer

            def __exit__(self, exc_type, exc, tb):
                self.outer._current_role = None
                return False

        return Ctx(self, role)

    def markdown(self, text):
        # Record rendered markdown under the current role (if any)
        self._messages_rendered.append({"role": self._current_role, "text": text})

    def chat_input(self, _label):
        return self._user_input

    def info(self, message):
        """Mock info method for streamlit"""
        pass
    
    def caption(self, text):
        """Mock caption method for streamlit"""
        pass
    
    def spinner(self, _text):
        class Spin:
            def __init__(self, outer):
                self.outer = outer

            def __enter__(self):
                self.outer._spinners.append(True)
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return Spin(self)


class FakeClient:
    def __init__(self, ok=True, answer="Resposta", error_msg="Erro"):
        self._ok = ok
        self._answer = answer
        self._error = error_msg
        self.calls = []

    def query(self, question: str, provider=None):
        self.calls.append(question)
        if self._ok:
            return {"ok": True, "data": {"answer": self._answer, "sources": [], "question": question}}
        return {"ok": False, "error": self._error}


def test_query_interface_initializes_state():
    from src.ui.pages.query_interface import render_page

    st = FakeSt(user_input=None)
    render_page(rag_client=FakeClient(), st=st)

    assert "messages" in st.session_state
    assert st.session_state["messages"] == []
    assert st._title_called is True


def test_query_interface_success_flow():
    from src.ui.pages.query_interface import render_page

    st = FakeSt(user_input="Olá?")
    client = FakeClient(ok=True, answer="Oi! Como posso ajudar?")
    render_page(rag_client=client, st=st)

    # Should add user and assistant messages
    assert len(st.session_state["messages"]) == 2
    assert st.session_state["messages"][0]["role"] == "user"
    assert st.session_state["messages"][1]["role"] == "assistant"
    assert any("Como posso ajudar" in m["content"] for m in st.session_state["messages"]) is True
    assert client.calls == ["Olá?"]


def test_query_interface_error_flow():
    from src.ui.pages.query_interface import render_page

    st = FakeSt(user_input="Pergunta que falha")
    client = FakeClient(ok=False, error_msg="Connection failed")
    render_page(rag_client=client, st=st)

    # Should include a friendly error message from assistant
    assert len(st.session_state["messages"]) == 2
    assert st.session_state["messages"][1]["role"] == "assistant"
    assert "Desculpe" in st.session_state["messages"][1]["content"]
