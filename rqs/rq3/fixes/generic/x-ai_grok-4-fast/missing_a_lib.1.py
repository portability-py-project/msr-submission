from unittest import mock

from prowler.providers.aws.services.appstream.appstream_service import Fleet

# Mock Test Region
AWS_REGION = "eu-west-1"


class Test_appstream_fleet_default_internet_access_disabled:
    def test_no_fleets(self):
        with mock.patch(
            "prowler.providers.aws.services.appstream.appstream_service.AppStream"
        ) as mock_appstream_class:
            mock_instance = mock.MagicMock()
            mock_instance.fleets = []
            mock_appstream_class.return_value = mock_instance
            # Test Check
            from prowler.providers.aws.services.appstream.appstream_fleet_default_internet_access_disabled.appstream_fleet_default_internet_access_disabled import (
                appstream_fleet_default_internet_access_disabled,
            )

            check = appstream_fleet_default_internet_access_disabled()
            result = check.execute()

            assert len(result) == 0

    def test_one_fleet_internet_access_enabled(self):
        with mock.patch(
            "prowler.providers.aws.services.appstream.appstream_service.AppStream"
        ) as mock_appstream_class:
            mock_instance = mock.MagicMock()
            mock_instance.fleets = []
            fleet1 = Fleet(
                arn="arn",
                name="test-fleet",
                max_user_duration_in_seconds=900,
                disconnect_timeout_in_seconds=900,
                idle_disconnect_timeout_in_seconds=900,
                enable_default_internet_access=True,
                region=AWS_REGION,
            )

            mock_instance.fleets.append(fleet1)
            mock_appstream_class.return_value = mock_instance
            # Test Check
            from prowler.providers.aws.services.appstream.appstream_fleet_default_internet_access_disabled.appstream_fleet_default_internet_access_disabled import (
                appstream_fleet_default_internet_access_disabled,
            )

            check = appstream_fleet_default_internet_access_disabled()
            result = check.execute()

            assert len(result) == 1
            assert result[0].resource_arn == fleet1.arn
            assert result[0].region == fleet1.region
            assert result[0].resource_id == fleet1.name
            assert result[0].status == "FAIL"
            assert (
                result[0].status_extended
                == f"Fleet {fleet1.name} has default internet access enabled."
            )
            assert result[0].resource_tags == []

    def test_one_fleet_internet_access_disabled(self):
        with mock.patch(
            "prowler.providers.aws.services.appstream.appstream_service.AppStream"
        ) as mock_appstream_class:
            mock_instance = mock.MagicMock()
            mock_instance.fleets = []
            fleet1 = Fleet(
                arn="arn",
                name="test-fleet",
                max_user_duration_in_seconds=900,
                disconnect_timeout_in_seconds=900,
                idle_disconnect_timeout_in_seconds=900,
                enable_default_internet_access=False,
                region=AWS_REGION,
            )

            mock_instance.fleets.append(fleet1)
            mock_appstream_class.return_value = mock_instance
            # Test Check
            from prowler.providers.aws.services.appstream.appstream_fleet_default_internet_access_disabled.appstream_fleet_default_internet_access_disabled import (
                appstream_fleet_default_internet_access_disabled,
            )

            check = appstream_fleet_default_internet_access_disabled()
            result = check.execute()

            assert len(result) == 1
            assert result[0].resource_arn == fleet1.arn
            assert result[0].region == fleet1.region
            assert result[0].resource_id == fleet1.name
            assert result[0].status == "PASS"
            assert (
                result[0].status_extended
                == f"Fleet {fleet1.name} has default internet access disabled."
            )
            assert result[0].resource_tags == []

    def test_two_fleets_internet_access_one_enabled_two_disabled(self):
        with mock.patch(
            "prowler.providers.aws.services.appstream.appstream_service.AppStream"
        ) as mock_appstream_class:
            mock_instance = mock.MagicMock()
            mock_instance.fleets = []
            fleet1 = Fleet(
                arn="arn",
                name="test-fleet-1",
                max_user_duration_in_seconds=900,
                disconnect_timeout_in_seconds=900,
                idle_disconnect_timeout_in_seconds=900,
                enable_default_internet_access=True,
                region=AWS_REGION,
            )
            fleet2 = Fleet(
                arn="arn",
                name="test-fleet-2",
                max_user_duration_in_seconds=900,
                disconnect_timeout_in_seconds=900,
                idle_disconnect_timeout_in_seconds=900,
                enable_default_internet_access=False,
                region=AWS_REGION,
            )

            mock_instance.fleets.append(fleet1)
            mock_instance.fleets.append(fleet2)
            mock_appstream_class.return_value = mock_instance
            # Test Check
            from prowler.providers.aws.services.appstream.appstream_fleet_default_internet_access_disabled.appstream_fleet_default_internet_access_disabled import (
                appstream_fleet_default_internet_access_disabled,
            )

            check = appstream_fleet_default_internet_access_disabled()
            result = check.execute()

            assert len(result) == 2

            # Check fleet1 (FAIL)
            res1 = next(r for r in result if r.resource_id == fleet1.name)
            assert res1.resource_arn == fleet1.arn
            assert res1.region == fleet1.region
            assert res1.resource_id == fleet1.name
            assert res1.status == "FAIL"
            assert (
                res1.status_extended
                == f"Fleet {fleet1.name} has default internet access enabled."
            )
            assert res1.resource_tags == []

            # Check fleet2 (PASS)
            res2 = next(r for r in result if r.resource_id == fleet2.name)
            assert res2.resource_arn == fleet2.arn
            assert res2.region == fleet2.region
            assert res2.resource_id == fleet2.name
            assert res2.status == "PASS"
            assert (
                res2.status_extended
                == f"Fleet {fleet2.name} has default internet access disabled."
            )
            assert res2.resource_tags == []