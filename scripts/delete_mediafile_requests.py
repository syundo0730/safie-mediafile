import argparse
import asyncio

from safie_mediafile import DeviceAPI, MediaFileAPI, async_client


async def main(args: argparse.Namespace):
    async with async_client(api_token=args.api_token) as client:
        device_api = DeviceAPI(client)
        device_id = await device_api.find_device_id(serial=args.serial)
        mediafile_api = MediaFileAPI(client)
        mediafile_requests = await mediafile_api.list_mediafile_requests(device_id)
        print(mediafile_requests)
        for request in mediafile_requests:
            await mediafile_api.delete_mediafile_request(device_id, request["request_id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", type=str, required=True)
    parser.add_argument("--api-token", type=str, required=True)
    args = parser.parse_args()
    asyncio.run(main(args))
