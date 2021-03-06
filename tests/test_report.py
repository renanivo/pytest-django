class TestQueryCount(object):
    """Test report generated by --querycount parameter"""

    def test_querycount_report_header(self, django_testdir):
        django_testdir.create_test_module('''
            def test_zero_queries():
                pass
        ''')

        result = django_testdir.runpytest_subprocess('--querycount=5')
        result.stdout.fnmatch_lines([
            '*== top 5 tests with most queries ==*'
        ])

    def test_header_not_set_without_parameter(self, django_testdir):
        django_testdir.create_test_module('''
            def test_zero_queries():
                pass
        ''')

        result = django_testdir.runpytest_subprocess()
        assert 'tests with most queries' not in result.stdout.str()

    def test_disabled_when_noquerycount_is_also_used(self, django_testdir):
        django_testdir.create_test_module('''
            def test_zero_queries():
                pass
        ''')

        result = django_testdir.runpytest_subprocess(
            '--querycount=5 --noquerycount'
        )
        assert 'tests with most queries' not in result.stdout.str()

    def test_query_optimization_tips_for_the_current_version_of_django(
        self,
        django_testdir
    ):
        django_testdir.create_test_module('''
            def test_zero_queries():
                pass
        ''')

        result = django_testdir.runpytest_subprocess('--querycount=5')

        import django
        major, minor = django.VERSION[0:2]

        url = (
            'https://docs.djangoproject.com'
            '/en/{major}.{minor}/topics/db/optimization/'
        ).format(
            major=major,
            minor=minor
        )

        assert url in result.stdout.str()

    def test_querycount_report_lines(self, django_testdir):
        django_testdir.create_test_module('''
            import pytest
            from django.db import connection

            @pytest.mark.django_db
            def test_one_query():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')

                assert True

            @pytest.mark.django_db
            def test_two_queries():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.execute('SELECT 1')

                assert True

            @pytest.mark.django_db
            def test_failed_one_query():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')

                assert False

            def test_zero_queries():
                assert True
        ''')

        result = django_testdir.runpytest_subprocess('--querycount=4')
        lines = result.stdout.get_lines_after(
            '*top 4 tests with most queries*'
        )
        assert 'test_two_queries' in lines[0]
        assert 'test_one_query' in lines[1]
        assert 'test_failed' in lines[2]
        assert 'test_zero_queries' in lines[3]

    def test_report_all_lines_on_querycount_zero(self, django_testdir):
        django_testdir.create_test_module('''
            import pytest
            from django.db import connection

            @pytest.mark.django_db
            def test_one_query():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')

                assert True

            @pytest.mark.django_db
            def test_two_queries():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.execute('SELECT 1')

                assert True
        ''')

        result = django_testdir.runpytest_subprocess('--querycount=0')
        lines = result.stdout.get_lines_after(
            '*top tests with most queries*'
        )
        assert 'test_two_queries' in lines[0]
        assert 'test_one_query' in lines[1]

    def test_should_report_fixture_queries(self, django_testdir):
        django_testdir.create_test_module('''
            import pytest
            from django.db import connection

            @pytest.fixture
            def one_query():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')

            @pytest.mark.django_db
            def test_without_queries(one_query):
                pass
        ''')

        result = django_testdir.runpytest_subprocess(
            '--setup-show',
            '--querycount=5'
        )

        assert '(# of queries executed: 1)' in result.stdout.str()
