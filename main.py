from cli import setup_cli, execute_command

def main():
    parser = setup_cli()
    args = parser.parse_args()
    execute_command(args)

if __name__ == '__main__':
    main()
