from Commands import rrc

def main():
    for _ in range(5):
        result = rrc.get_random_comment('nba')
        if result:
            print(result['comment_body'], result['comment_link'], f'\n')
        else:
            print("No result found.")


if __name__ == '__main__':
  main()

