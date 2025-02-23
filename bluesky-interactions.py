from datetime import datetime
import json
import csv
from atproto import Client, models
import time
from collections import defaultdict
import os
from dotenv import load_dotenv

class FollowerInteractionAnalyzer:
    def __init__(self, handle, app_password):
        self.client = Client()
        try:
            self.client.login(handle, app_password)
            print(f"Successfully logged in as {handle}")
        except Exception as e:
            print(f"Login failed: {str(e)}")
            raise e
        
        # Store follower interactions
        self.follower_interactions = defaultdict(lambda: {
            'likes': 0,
            'reposts': 0,
            'replies': 0,
            'total_interactions': 0,
            'last_interaction': None,
            'handle': '',
            'did': ''
        })
        
    def get_following(self):
        """Get list of accounts the user follows"""
        print("Getting list of accounts you follow...")
        cursor = None
        following = {}  # Store as dict for quick lookup
        count = 0
        
        while True:
            response = self.client.get_follows(self.client.me.did, cursor=cursor, limit=100)
            for follow in response.follows:
                following[follow.handle] = follow.did
                count += 1
                if count % 100 == 0:
                    print(f"Found {count} followed accounts...")
            
            if not response.cursor:
                break
            cursor = response.cursor
            time.sleep(0.5)  # Rate limiting
            
        print(f"You follow {len(following)} accounts")
        return following

    def process_post_interactions(self, post_uri, following):
        """Process all interactions for a single post"""
        try:
            # Get likes
            cursor = None
            try:
                response = self.client.get_likes(post_uri, cursor=cursor, limit=100)
                print(f"Found {len(response.likes)} likes")
                for like in response.likes:
                    if like.actor.handle in following:
                        self.follower_interactions[like.actor.handle]['likes'] += 1
                        self.follower_interactions[like.actor.handle]['total_interactions'] += 1
                        self.follower_interactions[like.actor.handle]['handle'] = like.actor.handle
                        self.follower_interactions[like.actor.handle]['did'] = like.actor.did
                        print(f"Recorded like from follower: {like.actor.handle}")
                        
                        interaction_time = datetime.strptime(like.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                        if (not self.follower_interactions[like.actor.handle]['last_interaction'] or 
                            interaction_time > datetime.strptime(self.follower_interactions[like.actor.handle]['last_interaction'], "%Y-%m-%dT%H:%M:%S.%fZ")):
                            self.follower_interactions[like.actor.handle]['last_interaction'] = like.created_at
                
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                print(f"Error fetching likes: {e}")

            # Get reposts
            try:
                response = self.client.get_reposted_by(post_uri)
                print(f"Found {len(response.reposted_by)} reposts")
                for repost in response.reposted_by:
                    if repost.handle in following:
                        self.follower_interactions[repost.handle]['reposts'] += 1
                        self.follower_interactions[repost.handle]['total_interactions'] += 1
                        self.follower_interactions[repost.handle]['handle'] = repost.handle
                        self.follower_interactions[repost.handle]['did'] = repost.did
                        print(f"Recorded repost from follower: {repost.handle}")
                        
                        interaction_time = datetime.strptime(repost.indexed_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                        if (not self.follower_interactions[repost.handle]['last_interaction'] or 
                            interaction_time > datetime.strptime(self.follower_interactions[repost.handle]['last_interaction'], "%Y-%m-%dT%H:%M:%S.%fZ")):
                            self.follower_interactions[repost.handle]['last_interaction'] = repost.indexed_at
                
                time.sleep(0.2)  # Rate limiting
            except Exception as e:
                print(f"Error fetching reposts: {e}")

            # Get replies
            try:
                thread = self.client.get_post_thread(post_uri)
                if hasattr(thread.thread, 'replies'):
                    print(f"Found {len(thread.thread.replies)} replies")
                    for reply in thread.thread.replies:
                        if reply.post.author.handle in following:
                            self.follower_interactions[reply.post.author.handle]['replies'] += 1
                            self.follower_interactions[reply.post.author.handle]['total_interactions'] += 1
                            self.follower_interactions[reply.post.author.handle]['handle'] = reply.post.author.handle
                            self.follower_interactions[reply.post.author.handle]['did'] = reply.post.author.did
                            print(f"Recorded reply from follower: {reply.post.author.handle}")
                            
                            interaction_time = datetime.strptime(reply.post.indexed_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                            if (not self.follower_interactions[reply.post.author.handle]['last_interaction'] or 
                                interaction_time > datetime.strptime(self.follower_interactions[reply.post.author.handle]['last_interaction'], "%Y-%m-%dT%H:%M:%S.%fZ")):
                                self.follower_interactions[reply.post.author.handle]['last_interaction'] = reply.post.indexed_at
            except Exception as e:
                print(f"Error fetching replies: {e}")

        except Exception as e:
            print(f"Error processing post: {e}")

    def analyze_all_posts(self):
        """Analyze all posts for interactions"""
        following = self.get_following()
        
        # Get all your posts
        print("\nFetching your posts...")
        cursor = None
        posts_analyzed = 0
        
        while True:
            try:
                feed = self.client.get_author_feed(self.client.me.did, cursor=cursor, limit=100)
                for post in feed.feed:
                    # Skip if this is a reply
                    if post.reply:
                        print(f"\nSkipping reply: {post.post.uri}")
                        continue
                        
                    posts_analyzed += 1
                    print(f"\nAnalyzing main post {posts_analyzed}")
                    print(f"Post URI: {post.post.uri}")
                    self.process_post_interactions(post.post.uri, following)
                    time.sleep(0.2)  # Rate limiting
                
                if not feed.cursor:
                    break
                cursor = feed.cursor
                time.sleep(1)  # Rate limiting between pages
                
            except Exception as e:
                print(f"Error fetching posts: {e}")
                break
        
        print(f"\nAnalyzed {posts_analyzed} posts")
        
        # Add any following accounts that had no interactions
        for handle, did in following.items():
            if handle not in self.follower_interactions:
                self.follower_interactions[handle] = {
                    'likes': 0,
                    'reposts': 0,
                    'replies': 0,
                    'total_interactions': 0,
                    'last_interaction': None,
                    'handle': handle,
                    'did': did
                }
        
        return dict(self.follower_interactions)  # Convert defaultdict to regular dict

def format_interactions(interactions):
    """Format interaction data into readable format"""
    # Convert to list of tuples so we can sort
    interaction_list = []
    for handle, data in interactions.items():
        interaction_list.append({
            'handle': handle,
            'total': data['total_interactions'],
            'last_date': data['last_interaction'] if data['last_interaction'] else "Never",
            'details': {
                'likes': data['likes'],
                'reposts': data['reposts'],
                'replies': data['replies']
            }
        })
    
    # Sort by total interactions and then by handle
    interaction_list.sort(key=lambda x: (-x['total'], x['handle']))
    
    # Format output
    formatted = "Interaction Analysis for All Followed Accounts\n"
    formatted += "=" * 100 + "\n\n"
    formatted += f"{'Handle':<40} {'Total':<8} {'Last Interaction':<25} {'Likes':<8} {'Reposts':<8} {'Replies':<8}\n"
    formatted += "-" * 100 + "\n"
    
    for entry in interaction_list:
        if entry['last_date'] != "Never":
            last_date = datetime.strptime(entry['last_date'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_date = "Never"
            
        formatted += f"{entry['handle']:<40} {entry['total']:<8} {last_date:<25} {entry['details']['likes']:<8} {entry['details']['reposts']:<8} {entry['details']['replies']:<8}\n"
    
    # Add summary statistics
    active_accounts = sum(1 for entry in interaction_list if entry['total'] > 0)
    total_interactions = sum(entry['total'] for entry in interaction_list)
    total_likes = sum(entry['details']['likes'] for entry in interaction_list)
    total_reposts = sum(entry['details']['reposts'] for entry in interaction_list)
    total_replies = sum(entry['details']['replies'] for entry in interaction_list)
    
    formatted += "\n" + "=" * 100 + "\n"
    formatted += f"Summary:\n"
    formatted += f"Total Accounts Followed: {len(interaction_list)}\n"
    formatted += f"Accounts That Have Interacted: {active_accounts}\n"
    formatted += f"Total Interactions: {total_interactions}\n"
    formatted += f"Total Likes: {total_likes}\n"
    formatted += f"Total Reposts: {total_reposts}\n"
    formatted += f"Total Replies: {total_replies}\n"
    
    return formatted

def export_to_csv(interactions, filename='follower_interactions.csv'):
    """Export interaction data to CSV format"""
    # Convert interaction data to list for sorting
    interaction_list = []
    for handle, data in interactions.items():
        last_date = data['last_interaction']
        if last_date:
            last_date = datetime.strptime(last_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_date = "Never"
            
        interaction_list.append({
            'Handle': handle,
            'Total_Interactions': data['total_interactions'],
            'Last_Interaction': last_date,
            'Likes': data['likes'],
            'Reposts': data['reposts'],
            'Replies': data['replies'],
            'DID': data['did']
        })
    
    # Sort by total interactions and then by handle
    interaction_list.sort(key=lambda x: (-x['Total_Interactions'], x['Handle']))
    
    # Write to CSV
    fieldnames = ['Handle', 'Total_Interactions', 'Last_Interaction', 'Likes', 'Reposts', 'Replies', 'DID']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(interaction_list)
        
        # Add blank row before summary
        writer.writerow(dict.fromkeys(fieldnames, ''))
        
        # Add summary statistics
        active_accounts = sum(1 for entry in interaction_list if entry['Total_Interactions'] > 0)
        total_interactions = sum(entry['Total_Interactions'] for entry in interaction_list)
        total_likes = sum(entry['Likes'] for entry in interaction_list)
        total_reposts = sum(entry['Reposts'] for entry in interaction_list)
        total_replies = sum(entry['Replies'] for entry in interaction_list)
        
        summary_rows = [
            {'Handle': 'SUMMARY', 'Total_Interactions': '', 'Last_Interaction': '', 'Likes': '', 'Reposts': '', 'Replies': '', 'DID': ''},
            {'Handle': 'Total Accounts Followed', 'Total_Interactions': len(interaction_list), 'Last_Interaction': '', 'Likes': '', 'Reposts': '', 'Replies': '', 'DID': ''},
            {'Handle': 'Accounts That Have Interacted', 'Total_Interactions': active_accounts, 'Last_Interaction': '', 'Likes': '', 'Reposts': '', 'Replies': '', 'DID': ''},
            {'Handle': 'Total Interactions', 'Total_Interactions': total_interactions, 'Last_Interaction': '', 'Likes': total_likes, 'Reposts': total_reposts, 'Replies': total_replies, 'DID': ''}
        ]
        
        writer.writerows(summary_rows)

def main():
    load_dotenv()
    #Input your Bluesky Handle here
    HANDLE = "YOURBSKYHANDLE"
    APP_PASSWORD = os.getenv('BLUESKY')
    
    analyzer = FollowerInteractionAnalyzer(HANDLE, APP_PASSWORD)
    interactions = analyzer.analyze_all_posts()
    
    # Format and save results
    formatted_output = format_interactions(interactions)
    
    # Save raw JSON
    with open('follower_interactions.json', 'w') as f:
        json.dump(interactions, f, indent=2)
    
    # Save formatted text
    with open('follower_interactions.txt', 'w', encoding='utf-8') as f:
        f.write(formatted_output)
    
    # Save CSV
    export_to_csv(interactions)
    
    # Print to console
    print(formatted_output)
    print(f"\nResults saved to follower_interactions.txt, follower_interactions.json, and follower_interactions.csv")

if __name__ == "__main__":
    main()
